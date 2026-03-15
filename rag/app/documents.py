import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import psycopg
from psycopg.rows import dict_row


class DocumentResolutionError(Exception):
    """Raised when the requested documents cannot be located."""


_DOC_ID_PATTERN = re.compile(r"^doc_(\d+)$", re.IGNORECASE)

_uploads_root_value = os.environ.get("UPLOADS_ROOT", "uploads")
UPLOADS_ROOT = os.path.abspath(_uploads_root_value)
STORE_ROOT = os.path.abspath(
    os.path.join(
        _uploads_root_value,
        os.environ.get("UPLOADS_STORE_SUBDIR", "files")
    )
)
CACHE_ROOT = os.path.abspath(
    os.path.join(
        _uploads_root_value,
        os.environ.get("UPLOADS_CACHE_SUBDIR", "cache")
    )
)


@dataclass
class ResolvedDocument:
    path: str
    name: str
    doc_id: Optional[str] = None


def resolve_documents(
    doc_refs: Sequence[Any],
    chat_id: Optional[Any] = None,
    case_id: Optional[Any] = None
) -> List[ResolvedDocument]:
    resolver = DocumentResolver()
    return resolver.resolve(doc_refs, chat_id=chat_id, case_id=case_id)


class DocumentResolver:
    def resolve(
        self,
        doc_refs: Sequence[Any],
        chat_id: Optional[Any] = None,
        case_id: Optional[Any] = None
    ) -> List[ResolvedDocument]:
        refs = list(doc_refs or [])
        if not refs:
            raise DocumentResolutionError("Список документов пуст.")

        expected_chat_id = str(chat_id) if chat_id is not None else None
        expected_case_id = self._normalize_case_id(case_id)

        resolved: List[Optional[ResolvedDocument]] = [None] * len(refs)
        pending: List[Tuple[int, int]] = []

        for idx, ref in enumerate(refs):
            entry = self._try_direct_path(ref)
            if entry:
                resolved[idx] = entry
                continue

            doc_id = self._extract_doc_id(ref)
            if doc_id is not None:
                pending.append((idx, doc_id))
                continue

            raise DocumentResolutionError(
                f"Не удалось распознать документ '{ref}'. Ожидается путь к файлу или doc_id."
            )

        if pending:
            rows = self._fetch_documents([doc_id for _, doc_id in pending])
            missing = [doc_id for _, doc_id in pending if doc_id not in rows]
            if missing:
                labels = ", ".join(f"doc_{doc_id}" for doc_id in missing)
                raise DocumentResolutionError(f"Документы не найдены в базе данных: {labels}.")

            for idx, doc_id in pending:
                row = rows[doc_id]
                self._validate_row(row, expected_chat_id, expected_case_id)
                resolved[idx] = self._entry_from_row(row)

        return [entry for entry in resolved if entry]

    def _extract_doc_id(self, ref: Any) -> Optional[int]:
        candidate: Optional[Any] = None
        if isinstance(ref, dict):
            for key in ("doc_id", "id"):
                if key in ref:
                    candidate = ref[key]
                    break
        else:
            candidate = ref

        if candidate is None:
            return None

        value = str(candidate).strip()
        if not value:
            return None

        match = _DOC_ID_PATTERN.match(value)
        if match:
            return int(match.group(1))

        if value.isdigit():
            return int(value)

        return None

    def _try_direct_path(self, ref: Any) -> Optional[ResolvedDocument]:
        raw_path: Optional[str] = None
        label: Optional[str] = None
        doc_id: Optional[str] = None

        if isinstance(ref, dict):
            raw_path = ref.get("path") or ref.get("file") or ref.get("file_path")
            label = ref.get("name") or ref.get("filename")
            doc_id = ref.get("doc_id")
        elif isinstance(ref, (str, os.PathLike)):
            raw_path = str(ref).strip()
        else:
            return None

        if not raw_path:
            return None

        for candidate in self._candidate_paths(raw_path):
            if candidate and os.path.exists(candidate):
                resolved_label = label or os.path.basename(candidate)
                normalized_doc_id = self._format_doc_id(doc_id)
                return ResolvedDocument(
                    path=os.path.abspath(candidate),
                    name=resolved_label,
                    doc_id=normalized_doc_id
                )

        return None

    def _candidate_paths(self, raw_path: str) -> List[str]:
        normalized = raw_path.strip().lstrip("./\\")
        lowered = normalized.lower()
        candidates: List[str] = []

        if os.path.isabs(raw_path):
            candidates.append(raw_path)
            return candidates

        candidates.append(os.path.abspath(normalized))

        if not lowered.startswith("uploads/"):
            candidates.append(os.path.abspath(os.path.join(UPLOADS_ROOT, normalized)))

        if not (lowered.startswith("uploads/files/") or lowered.startswith("files/")):
            candidates.append(os.path.abspath(os.path.join(STORE_ROOT, normalized)))

        if not (lowered.startswith("uploads/cache/") or lowered.startswith("cache/")):
            candidates.append(os.path.abspath(os.path.join(CACHE_ROOT, normalized)))

        unique: List[str] = []
        seen = set()
        for candidate in candidates:
            key = os.path.normcase(candidate)
            if key not in seen:
                seen.add(key)
                unique.append(candidate)

        return unique

    def _normalize_case_id(self, case_id: Optional[Any]) -> Optional[int]:
        if case_id is None:
            return None
        value = str(case_id).strip()
        if not value:
            return None
        if value.lower().startswith("case_"):
            value = value.split("_", 1)[1]
        return int(value) if value.isdigit() else None

    def _validate_row(
        self,
        row: Dict[str, Any],
        expected_chat_id: Optional[str],
        expected_case_id: Optional[int]
    ) -> None:
        if expected_case_id is not None:
            row_case_id = int(row.get("case_id"))
            if row_case_id != expected_case_id:
                raise DocumentResolutionError(
                    f"doc_{row['id']} относится к другому делу (ожидалось case_{expected_case_id})."
                )

        if expected_chat_id is not None:
            row_chat_id = row.get("chat_id")
            if row_chat_id is None or str(row_chat_id) != expected_chat_id:
                raise DocumentResolutionError(
                    f"doc_{row['id']} не принадлежит чату {expected_chat_id}."
                )

    def _fetch_documents(self, doc_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        if not doc_ids:
            return {}

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT documents.id,
                               documents.case_id,
                               documents.file_data,
                               cases.chat_id
                        FROM documents
                        JOIN cases ON cases.id = documents.case_id
                        WHERE documents.id = ANY(%s)
                        """,
                        (doc_ids,)
                    )
                    rows = cur.fetchall()
        except psycopg.Error as exc:
            raise DocumentResolutionError(f"Ошибка подключения к базе данных: {exc}") from exc

        return {int(row["id"]): row for row in rows}

    def _entry_from_row(self, row: Dict[str, Any]) -> ResolvedDocument:
        raw_data = row.get("file_data")
        info = self._parse_file_data(raw_data)
        if not info:
            raise DocumentResolutionError(f"Для doc_{row['id']} отсутствует file_data.")

        storage = info.get("storage", "store")
        rel_path = str(info.get("id") or "").lstrip("/\\")
        if not rel_path:
            raise DocumentResolutionError(f"Для doc_{row['id']} отсутствует путь к файлу.")

        metadata = info.get("metadata") or {}
        filename = metadata.get("filename") or f"document_{row['id']}"

        root = STORE_ROOT if storage == "store" else CACHE_ROOT
        file_path = self._safe_join(root, rel_path)

        if not os.path.exists(file_path):
            raise DocumentResolutionError(
                f"Файл для doc_{row['id']} не найден по пути {file_path}."
            )

        return ResolvedDocument(
            path=file_path,
            name=filename,
            doc_id=f"doc_{row['id']}"
        )

    def _parse_file_data(self, raw_data: Any) -> Optional[Dict[str, Any]]:
        if not raw_data:
            return None
        if isinstance(raw_data, dict):
            return raw_data
        if isinstance(raw_data, (bytes, bytearray)):
            raw_data = raw_data.decode("utf-8")
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError as exc:
            raise DocumentResolutionError("Не удалось прочитать file_data документа.") from exc

    def _safe_join(self, root: str, relative_path: str) -> str:
        normalized_relative = relative_path.lstrip("/\\")
        candidate = os.path.abspath(os.path.join(root, normalized_relative))
        root_abs = os.path.abspath(root)
        if not os.path.commonpath([candidate, root_abs]) == root_abs:
            raise DocumentResolutionError("Получен недопустимый путь для файла документа.")
        return candidate

    def _format_doc_id(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        parsed = self._extract_doc_id(value)
        return f"doc_{parsed}" if parsed is not None else None

    def _connect(self):
        dsn = os.environ.get("DATABASE_URL")
        try:
            if dsn:
                return psycopg.connect(dsn, row_factory=dict_row)

            host = os.environ.get("DATABASE_HOST", "localhost")
            port = int(os.environ.get("DATABASE_PORT", "5432"))
            dbname = os.environ.get("DATABASE_NAME", "development")
            user = os.environ.get("DATABASE_USER", "user")
            password = os.environ.get("DATABASE_PASSWORD", "password")

            return psycopg.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                row_factory=dict_row
            )
        except psycopg.Error as exc:
            raise DocumentResolutionError(f"Не удалось подключиться к базе данных: {exc}") from exc
