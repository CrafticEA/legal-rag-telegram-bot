# frozen_string_literal: true

class RagAskService
  def initialize(legal_case:, question:)
    @legal_case = legal_case
    @question = question
  end

  def call
    # TODO: integrate with RAG and LLM services
    {
      answer: "Ответ по документам дела (вопрос: #{@question}). Интеграция с RAG в разработке.",
      citations: []
    }
  end
end
