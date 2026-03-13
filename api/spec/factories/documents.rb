# frozen_string_literal: true

FactoryBot.define do
  factory :document do
    association :case
    # file is optional; for upload tests we pass file in the request
  end
end
