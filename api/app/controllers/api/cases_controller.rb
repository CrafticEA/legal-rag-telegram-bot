module Api
  class CasesController < ApplicationController

    # GET api/cases
    def index
      @cases = Case.ransack(case_sorted_params).result
    end

    # POST api/cases
    def create
      @case = Case.create!(chat_id: params[:chat_id], status: 'pending')
    end

    # POST api/cases/:case_id/documents
    def documents
      @case = Case.find(params[:id])
      @document = Document.new(case_id: @case.id, file: params[:file])
      @document.save
    end

    # GET api/cases/:case_id/status
    def status
      @case = Case.find(params[:id])
    end

    private

    def case_sorted_params
      {
        chat_id_eq: params[:chat_id]
      }
    end
  end
end