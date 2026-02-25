Rails.application.routes.draw do

  namespace :api, defaults: { format: :json } do
    resources :cases, only: [:create, :index] do
      resources :documents, only: [:create]
      get :status, on: :member
    end
  end
end
