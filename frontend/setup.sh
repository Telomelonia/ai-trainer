if [ ! -f "package.json" ]; then
    npx create-next-app@latest . --typescript --use-yarn --no-install --yes
fi
yarn install
yarn add next@latest react@latest react-dom@latest
yarn dev -p 8080