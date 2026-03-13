# frozen_string_literal: true

class AddTitleAndProgressToCases < ActiveRecord::Migration[8.0]
  def change
    add_column :cases, :title, :string
    add_column :cases, :progress, :integer, default: 0, null: false
  end
end
