class Document < ApplicationRecord
  include DocumentUploader::Attachment(:file)
  belongs_to :case

  def file_url
    return nil unless file&.url

    host = Services.website&.host
    host ? "#{host}#{file.url}" : file.url.to_s
  end

  def doc_id
    "doc_#{id}"
  end

  def file_name
    file&.original_filename || file&.metadata&.dig('filename') || 'document'
  end

  def mime_type
    file&.mime_type || file&.metadata&.dig('mime_type') || 'application/octet-stream'
  end

  def size_bytes
    file&.size || file&.metadata&.dig('size') || 0
  end
end
