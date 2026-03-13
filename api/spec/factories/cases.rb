# frozen_string_literal: true

FactoryBot.define do
  factory :case, class: "Case" do
    chat_id { "123456789" }
    status { "READY" }
    title { "Тестовое дело" }
    progress { 100 }

    trait :empty do
      status { "EMPTY" }
      progress { 0 }
    end

    trait :dirty do
      status { "DIRTY" }
    end
  end
end
