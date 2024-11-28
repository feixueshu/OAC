#!/bin/bash

# 設定を読み込み
source ./merge_config.sh

# SemanticModelMain ディレクトリが存在するか確認
if [ ! -d "SemanticModelMain" ]; then
  # メインリポジトリをクローン
  git clone $MAIN_REPO
fi

# SemanticModelMain ディレクトリに移動
cd SemanticModelMain || exit 1

# ProjectA と ProjectB をメインリポジトリのサブディレクトリに subtree で追加
git subtree add --prefix=projectA $PROJECTA_REPO $PROJECTA_BRANCH --squash
git subtree add --prefix=projectB $PROJECTB_REPO $PROJECTB_BRANCH --squash

# ProjectA と ProjectB をメインリポジトリのルートディレクトリに統合
rsync -a projectA/ ./
rsync -a projectB/ ./

# 不要な .DS_Store ファイルを削除
find . -name ".DS_Store" -exec rm -f {} +

# 一時ファイルを削除
rm -rf projectA projectB

# 変更を追加してコミット
git add .
git commit -m "ProjectAとProjectBの内容をメインフォルダに統合"

# リモートのメインブランチにプッシュ
git push origin $MAIN_BRANCH

echo "同期と統合が正常に完了しました。"
