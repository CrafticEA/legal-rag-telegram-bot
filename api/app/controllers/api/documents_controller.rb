# frozen_string_literal: true

module Api
  class DocumentsController < ApplicationController
    include ParseCaseId
    before_action :set_case

    # POST api/cases/:case_id/documents (multipart/form-data, field: file)
    def create
      @document = @case.documents.build(document_params)
      if @document.save
        render json: { doc_id: document_id(@document), ok: true }, status: :created
      else
        render json: { errors: @document.errors.full_messages }, status: :unprocessable_entity
      end
    end

    # DELETE api/cases/:case_id/documents/:id
    def destroy
      @document = @case.documents.find(params[:id])
      doc_id = document_id(@document)
      @document.destroy
      @case.update!(status: 'DIRTY')
      render json: { ok: true, doc_id: doc_id, case_status: @case.status }
    end

    private

    def set_case
      @case = Case.find(parse_case_id_param(params[:case_id]))
    end

    def document_params
      params.permit(:file).slice(:file).to_h
    end

    def document_id(document)
      document.doc_id
    end
  end
end
