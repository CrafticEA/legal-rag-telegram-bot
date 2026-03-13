class Document < ApplicationRecord
  include DocumentUploader::Attachment(:file)
  belongs_to :case

  def file_url
    return nil unless file&.url

    host = Services.website&.host
    host ? "#{host}#{file.url}" : file.url.to_s
  end
end