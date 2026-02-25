class Case < ApplicationRecord
  has_many :documents, dependent: :destroy

  def self.ransackable_attributes(_auth_object = nil)
    ["chat_id", "created_at", "id", "status", "updated_at"]
  end
end
