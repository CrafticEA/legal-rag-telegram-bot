json.cases do
  json.array! @cases do |item|
    json.case_id "case_#{item.id}"
    json.title item.display_title
    json.status item.status
    json.documents_count item.documents.size
  end
end
