Rails.application.routes.draw do

  namespace :api, defaults: { format: :json } do
    resources :cases, only: [:create, :index, :show] do
      resources :documents, only: [:create, :destroy]
      get :status, on: :member
      post :ask, on: :member
    end
  end
end
