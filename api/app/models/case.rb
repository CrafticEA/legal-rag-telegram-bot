# frozen_string_literal: true

class Case < ApplicationRecord
  include DocumentUploader::Attachment(:faiss_index)
  include DocumentUploader::Attachment(:chunks)

  has_many :documents, dependent: :destroy

  def index_files_present?
    faiss_index.exists? && chunks.exists?
  end

  def self.ransackable_attributes(_auth_object = nil)
    ["chat_id", "created_at", "id", "status", "title", "progress", "updated_at"]
  end

  def display_title
    title.presence || "Дело #{id}"
  end
end
