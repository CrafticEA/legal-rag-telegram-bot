# frozen_string_literal: true

require "net/http"
require "json"

class RagAskService
  TOP_K = 6

  def initialize(legal_case:, question:)
    @legal_case = legal_case
    @question = question
  end

  def call
    chunks = call_retriever
    return error_response("RAG: релевантные фрагменты не найдены") if chunks.blank?

    call_generate(chunks)
  rescue RagAskService::HttpError => e
    error_response("Сервис временно недоступен: #{e.message}")
  end

  private

  def call_retriever
    uri = URI("#{Services.rag_url.chomp('/')}/retrieve")
    req = Net::HTTP::Post.new(uri)
    req["Content-Type"] = "application/json"
    req.body = {
      chat_id: @legal_case.chat_id.to_s,
      case_id: case_id_str,
      query: @question,
      top_k: TOP_K
    }.to_json

    res = do_http(uri, req)
    data = JSON.parse(res.body)
    data["chunks"]
  end

  def call_generate(chunks)
    uri = URI("#{Services.llm_url.chomp('/')}/generate")
    req = Net::HTTP::Post.new(uri)
    req["Content-Type"] = "application/json"
    req.body = {
      case_id: case_id_str,
      query: @question,
      chunks: chunks.map { |c| chunk_for_llm(c) }
    }.to_json

    res = do_http(uri, req)
    data = JSON.parse(res.body)

    {
      answer: data["answer"],
      sources: data["sources"] || [],
      meta: data["meta"] || {}
    }
  end

  def chunk_for_llm(c)
    {
      text: c["text"],
      source: c["source"],
      page: c["page"],
      chunk_id: c["chunk_id"],
      score: c["score"]
    }.compact
  end

  def case_id_str
    "case_#{@legal_case.id}"
  end

  def do_http(uri, req)
    res = Net::HTTP.start(uri.hostname, uri.port, use_ssl: uri.scheme == "https", open_timeout: 10, read_timeout: 60) do |http|
      http.request(req)
    end
    raise HttpError, "HTTP #{res.code}" unless res.is_a?(Net::HTTPSuccess)

    res
  end

  def error_response(message)
    {
      answer: message,
      sources: [],
      meta: { error: true }
    }
  end

  class HttpError < StandardError; end
end
