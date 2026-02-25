class Document < ApplicationRecord
  include DocumentUploader::Attachment(:file)
  belongs_to :case

  def file_url
    file&.url&.to_s ? "#{Services.website.host}#{file.url}" : nil
  end
end
