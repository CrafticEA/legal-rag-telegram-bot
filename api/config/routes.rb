Rails.application.routes.draw do

  namespace :api, defaults: { format: :json } do
    resources :cases, only: [:create, :index, :show] do
      resources :documents, only: [:create, :destroy]
      get :status, on: :member
      post :ask, on: :member
      post :upload_index, on: :member
      get :faiss_index, on: :member
      get :chunks, on: :member
    end
  end
end
