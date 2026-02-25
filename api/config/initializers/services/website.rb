require 'website'

class Services
  def website(env: Rails.env)
    case env
    when 'production'
      Website.new(
        host: 'http://localhost'
      )
    when 'staging'
      Website.new(
        host: 'http://localhost'
      )
    when 'development', 'test'
      Website.new(
        host: 'http://localhost'
      )
    else
      raise
    end
  end
  cattr_reader(:website, instance_reader: false, default: new.website)
end