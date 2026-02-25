class CreateCases < ActiveRecord::Migration[8.0]
  def change
    create_table :cases do |t|
      t.string :chat_id
      t.string :status

      t.timestamps
    end
  end
end
