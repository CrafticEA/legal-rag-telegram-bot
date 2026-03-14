# frozen_string_literal: true

class AddIndexAttachmentsToCases < ActiveRecord::Migration[8.0]
  def change
    add_column :cases, :faiss_index_data, :text
    add_column :cases, :chunks_data, :text
  end
end
