# frozen_string_literal: true

module Api
  class CasesController < ApplicationController
    include ParseCaseId
    before_action :set_case, only: [:upload_index, :faiss_index, :chunks]

    # GET api/cases?chat_id=123456789
    def index
      cases = Case.ransack(case_sorted_params).result.includes(:documents)

      render json: {
        cases: cases.map { |item|
          {
            case_id: "case_#{item.id}",
            title: item.display_title,
            status: item.status,
            documents_count: item.documents.size
          }
        }
      }
    end

    # GET api/cases/:id?chat_id=123456789 (id может быть case_123)
    def show
      @case = Case.where(chat_id: params[:chat_id]).find(parse_case_id_param(params[:id]))
    end

    # POST api/cases
    def create
      @case = Case.create!(chat_id: params[:chat_id], status: 'EMPTY')
    end

    # GET api/cases/:id/status?chat_id=123456789 (id может быть case_123)
    def status
      @case = Case.where(chat_id: params[:chat_id]).find(parse_case_id_param(params[:id]))
    end

    # POST api/cases/:id/ask (RAG, id может быть case_123)
    def ask
      @case = Case.where(chat_id: params[:chat_id]).find(parse_case_id_param(params[:id]))
      question = params[:question].to_s
      result = RagAskService.new(legal_case: @case, question: question).call
      render json: result, status: :ok
    end

    # POST api/cases/:id/upload_index — загрузка faiss.index и chunks (как у documents, через Shrine)
    # multipart: faiss_index, chunks
    def upload_index
      saved = {}
      @case.faiss_index = params[:faiss_index] if params[:faiss_index].respond_to?(:tempfile)
      saved[:faiss_index] = true if params[:faiss_index].respond_to?(:tempfile)
      @case.chunks = params[:chunks] if params[:chunks].respond_to?(:tempfile)
      saved[:chunks] = true if params[:chunks].respond_to?(:tempfile)

      if saved.empty?
        return render json: { ok: false, error: "Нужно передать файлы faiss_index и/или chunks" }, status: :unprocessable_entity
      end

      @case.save!
      @case.update!(status: "READY") if @case.index_files_present?

      render json: {
        ok: true,
        case_id: "case_#{@case.id}",
        case_status: @case.status,
        saved: saved
      }, status: :created
    end

    # GET api/cases/:id/faiss_index — скачать faiss.index по делу (как document)
    def faiss_index
      unless @case.faiss_index.exists?
        return render json: { error: "Индекс не найден" }, status: :not_found
      end
      send_data @case.faiss_index.read,
                filename: "faiss.index",
                type: "application/octet-stream",
                disposition: "attachment"
    end

    # GET api/cases/:id/chunks — скачать chunks по делу (как document)
    def chunks
      unless @case.chunks.exists?
        return render json: { error: "Чанки не найдены" }, status: :not_found
      end
      send_data @case.chunks.read,
                filename: "chunks.jsonl",
                type: "application/x-ndjson",
                disposition: "attachment"
    end

    private

    def set_case
      @case = Case.find(parse_case_id_param(params[:id]))
    end

    def case_sorted_params
      {
        chat_id_eq: params[:chat_id]
      }
    end
  end
end