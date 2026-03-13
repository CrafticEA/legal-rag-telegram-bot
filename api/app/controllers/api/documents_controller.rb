module Api
  class DocumentsController < ApplicationController
    def create
      kase = Case.find(params[:case_id])
      document = Document.create!(case: kase, file: params[:file])

      render json: {
        id: document.id,
        case_id: kase.id,
        file_url: document.file_url
      }, status: :created
    end
  end
end