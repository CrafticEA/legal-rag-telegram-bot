module Api
  class CasesController < ApplicationController

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

    # GET api/cases/:id?chat_id=123456789
    def show
      @case = Case.where(chat_id: params[:chat_id]).find(params[:id])
    end

    # POST api/cases
    def create
      @case = Case.create!(chat_id: params[:chat_id], status: 'EMPTY')
    end

    # GET api/cases/:id/status?chat_id=123456789
    def status
      @case = Case.where(chat_id: params[:chat_id]).find(params[:id])
    end

    # POST api/cases/:id/ask (RAG)
    def ask
      @case = Case.where(chat_id: params[:chat_id]).find(params[:id])
      question = params[:question].to_s
      result = RagAskService.new(legal_case: @case, question: question).call
      render json: result, status: :ok
    end

    private

    def case_sorted_params
      {
        chat_id_eq: params[:chat_id]
      }
    end
  end
end