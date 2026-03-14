require_relative "boot"

require "rails/all"

Bundler.require(*Rails.groups)

module DsBackend
  class Application < Rails::Application
    config.load_defaults 8.0
    config.autoload_lib(ignore: %w[assets tasks])
    config.eager_load = true
    config.eager_load_paths << Rails.root.join('lib')
    config.autoload_paths << Rails.root.join('lib')
    config.api_only = true
  end
end
