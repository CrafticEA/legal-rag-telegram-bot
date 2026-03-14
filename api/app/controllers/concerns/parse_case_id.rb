# frozen_string_literal: true

module ParseCaseId
  private

  # Извлекает числовой id из "case_123" или оставляет число как есть
  def parse_case_id_param(value)
    return value if value.blank?
    str = value.to_s
    str.start_with?("case_") ? str.delete_prefix("case_").to_i : str.to_i
  end
end
