json.case_id "case_#{@case.id}"
json.status @case.status
json.progress @case.progress.to_i
