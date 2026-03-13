# frozen_string_literal: true

require "rails_helper"

RSpec.describe "Api::Cases", type: :request do
  let(:chat_id) { "123456789" }
  let(:auth_params) { { chat_id: chat_id } }

  describe "GET /api/cases" do
    context "with chat_id" do
      before do
        create_list(:case, 2, chat_id: chat_id)
      end

      it "returns list of cases" do
        get api_cases_path, params: auth_params, as: :json

        expect(response).to have_http_status(:success)
        body = response.parsed_body
        expect(body).to have_key("cases")
        expect(body["cases"]).to be_a(Array)
        expect(body["cases"].size).to be >= 2

        first = body["cases"].first
        expect(first).to have_key("case_id")
        expect(first["case_id"]).to match(/\Acase_\d+\z/)
        expect(first).to have_key("title")
        expect(first).to have_key("status")
        expect(first).to have_key("documents_count")
        expect(first["documents_count"]).to be_a(Integer)
      end
    end

    context "without chat_id" do
      it "returns success with cases array" do
        get api_cases_path, as: :json

        expect(response).to have_http_status(:success)
        expect(response.parsed_body).to have_key("cases")
      end
    end
  end

  describe "GET /api/cases/:id" do
    let(:case_record) { create(:case, chat_id: chat_id) }

    it "returns case with documents" do
      create(:document, case: case_record)

      get "#{api_case_path(case_record)}?chat_id=#{chat_id}", as: :json

      expect(response).to have_http_status(:success)
      body = response.parsed_body
      expect(body["case_id"]).to eq("case_#{case_record.id}")
      expect(body).to have_key("title")
      expect(body).to have_key("status")
      expect(body).to have_key("documents")
      expect(body["documents"]).to be_a(Array)

      body["documents"].each do |doc|
        expect(doc).to have_key("doc_id")
        expect(doc).to have_key("name")
        expect(doc).to have_key("mime_type")
        expect(doc).to have_key("size_bytes")
      end
    end

    context "with wrong chat_id" do
      it "returns 404" do
        get api_case_path(case_record), params: { chat_id: "999999999" }, as: :json

        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe "GET /api/cases/:id/status" do
    let(:case_record) { create(:case, chat_id: chat_id, status: "READY", progress: 100) }

    it "returns status and progress" do
      get "#{status_api_case_path(case_record)}?chat_id=#{chat_id}", as: :json

      expect(response).to have_http_status(:success)
      body = response.parsed_body
      expect(body["case_id"]).to eq("case_#{case_record.id}")
      expect(body).to have_key("status")
      expect(body).to have_key("progress")
      expect(body["progress"]).to be_a(Integer)
    end

    context "with wrong chat_id" do
      it "returns 404" do
        get status_api_case_path(case_record), params: { chat_id: "999999999" }, as: :json

        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe "POST /api/cases" do
    it "creates case with EMPTY status" do
      expect {
        post api_cases_path, params: { chat_id: "111222333" }, as: :json
      }.to change(Case, :count).by(1)

      expect(response).to have_http_status(:success)
      body = response.parsed_body
      expect(body).to have_key("case_id")
      expect(body["case_id"]).to match(/\Acase_\d+\z/)
      expect(body["status"]).to eq("EMPTY")
    end
  end

  describe "POST /api/cases/:id/ask" do
    let(:case_record) { create(:case, chat_id: chat_id) }

    it "returns answer and citations" do
      post ask_api_case_path(case_record),
           params: { chat_id: chat_id, question: "Какие риски?" },
           as: :json

      expect(response).to have_http_status(:success)
      body = response.parsed_body
      expect(body).to have_key("answer")
      expect(body).to have_key("citations")
      expect(body["citations"]).to be_a(Array)
    end

    context "with wrong chat_id" do
      it "returns 404" do
        post ask_api_case_path(case_record),
             params: { chat_id: "999999999", question: "Test" },
             as: :json

        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe "POST /api/cases/:case_id/documents" do
    let(:case_record) { create(:case, chat_id: chat_id) }

    it "uploads file and returns doc_id" do
      file = fixture_file_upload("sample.txt", "text/plain")

      expect {
        post api_case_documents_path(case_record), params: { chat_id: chat_id, file: file }
      }.to change(Document, :count).by(1)

      expect(response).to have_http_status(:created)
      body = response.parsed_body
      expect(body["ok"]).to be true
      expect(body).to have_key("doc_id")
      expect(body["doc_id"]).to match(/\Adoc_\d+\z/)
    end

    context "with wrong chat_id" do
      it "returns 404" do
        file = fixture_file_upload("sample.txt", "text/plain")

        post api_case_documents_path(case_record),
             params: { chat_id: "999999999", file: file }

        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe "DELETE /api/cases/:case_id/documents/:id" do
    let(:case_record) { create(:case, chat_id: chat_id, status: "READY") }
    let!(:document) { create(:document, case: case_record) }

    it "removes document and sets case status to DIRTY" do
      expect(case_record.documents).to include(document)

      delete api_case_document_path(case_record, document), params: auth_params, as: :json

      expect(response).to have_http_status(:success)
      body = response.parsed_body
      expect(body["ok"]).to be true
      expect(body["doc_id"]).to eq("doc_#{document.id}")
      expect(body["case_status"]).to eq("DIRTY")

      case_record.reload
      expect(case_record.status).to eq("DIRTY")
      expect(Document.exists?(document.id)).to be false
    end

    context "with wrong chat_id" do
      it "returns 404" do
        delete api_case_document_path(case_record, document),
               params: { chat_id: "999999999" },
               as: :json

        expect(response).to have_http_status(:not_found)
      end
    end
  end
end
