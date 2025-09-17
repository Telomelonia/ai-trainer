if [ ! -f "config/application.rb" ]; then
    rails new . --api --database=postgresql --skip-bundle
fi
bundle install
bundle exec rails credentials:edit || EDITOR="touch" bundle exec rails credentials:edit
RAILS_ENV=development bundle exec rails server -b 0.0.0.0