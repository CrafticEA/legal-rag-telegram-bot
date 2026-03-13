class Case < ApplicationRecord
  has_many :documents, dependent: :destroy

  def self.ransackable_attributes(_auth_object = nil)
    ["chat_id", "created_at", "id", "status", "title", "progress", "updated_at"]
  end

  def display_title
    title.presence || "Дело #{id}"
  end
end
