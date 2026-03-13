json.case_id "case_#{@case.id}"
json.title @case.display_title
json.status @case.status
json.documents @case.documents do |doc|
  json.doc_id doc.doc_id
  json.name doc.file_name
  json.mime_type doc.mime_type
  json.size_bytes doc.size_bytes
end
