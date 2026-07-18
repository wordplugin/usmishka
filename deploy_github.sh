#!/bin/bash
# usmishka サイトを github.com/wordplugin/usmishka に公開するスクリプト
# 前提: GitHub CLI (gh) がインストール済みで、wordplugin アカウントでログイン済みであること
#   インストール: brew install gh
#   ログイン:     gh auth login
set -e
cd "$(dirname "$0")"

# 1. リポジトリ初期化(初回のみ。既にあればスキップされる)
if [ ! -d .git ]; then
  git init -b main
fi

# 2. コミット
git add -A
git commit -m "Update usmishka website" || echo "変更なし(コミットスキップ)"

# 3. リモートが未設定なら wordplugin/usmishka を新規作成してpush、設定済みならpushのみ
if ! git remote get-url origin >/dev/null 2>&1; then
  gh repo create wordplugin/usmishka --public --source=. --remote=origin --push
else
  git push -u origin main
fi

# 4. (任意) GitHub Pagesで公開する場合は初回のみ下記を実行
#    公開URL: https://wordplugin.github.io/usmishka/
# gh api repos/wordplugin/usmishka/pages --method POST -f "source[branch]=main" -f "source[path]=/" 2>/dev/null || true

echo "完了: https://github.com/wordplugin/usmishka"
