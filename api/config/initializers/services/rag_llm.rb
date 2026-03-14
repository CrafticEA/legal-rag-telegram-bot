# frozen_string_literal: true

class Services
  class << self
    def rag_url
      ENV.fetch("RAG_URL", "http://localhost:8001")
    end

    def llm_url
      ENV.fetch("LLM_URL", "http://localhost:8002")
    end
  end
end
