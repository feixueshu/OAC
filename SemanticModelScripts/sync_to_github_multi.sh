#!/bin/bash

# 少なくとも1つの設定ファイルが渡されたか確認
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <config_file1> <config_file2> ..."
  exit 1
fi

# SemanticModelMainの相対パスを定義
SEMANTIC_MODEL_DIR="./SemanticModelMain"

# 一時同期用ディレクトリを作成
TEMP_DIR="./temp_sync"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# 各設定ファイルをループ処理
for CONFIG_FILE in "$@"; do
  # 設定ファイルを読み込み
  source ./$CONFIG_FILE

  # 設定ファイル内の変数が設定されているか確認
  if [ -z "$PhysicalLayerSchema" ] || [ -z "$PhysicalLayerDataSource" ] || [ -z "$LogicalLayerBusinessModel" ] || [ -z "$PresentationLayerSubject" ] || [ -z "$GitHubRepository" ] || [ -z "$Branch" ]; then
    echo "Error: Missing required variables in $CONFIG_FILE"
    exit 1
  fi

  # 指定されたファイルとフォルダを一時ディレクトリに抽出
  mkdir -p $TEMP_DIR/physical/$PhysicalLayerDataSource
  cp -r $SEMANTIC_MODEL_DIR/physical/$PhysicalLayerDataSource/$PhysicalLayerSchema $TEMP_DIR/physical/$PhysicalLayerDataSource/$PhysicalLayerSchema/
  cp $SEMANTIC_MODEL_DIR/physical/$PhysicalLayerDataSource/$PhysicalLayerSchema.json $TEMP_DIR/physical/$PhysicalLayerDataSource/
  cp $SEMANTIC_MODEL_DIR/physical/$PhysicalLayerDataSource.json $TEMP_DIR/physical/

  mkdir -p $TEMP_DIR/logical
  cp -r $SEMANTIC_MODEL_DIR/logical/$LogicalLayerBusinessModel $TEMP_DIR/logical/
  cp $SEMANTIC_MODEL_DIR/logical/$LogicalLayerBusinessModel.json $TEMP_DIR/logical/

  mkdir -p $TEMP_DIR/presentation
  cp -r $SEMANTIC_MODEL_DIR/presentation/$PresentationLayerSubject $TEMP_DIR/presentation/
  cp $SEMANTIC_MODEL_DIR/presentation/$PresentationLayerSubject.json $TEMP_DIR/presentation/

  echo "$CONFIG_FILE の指定されたファイルとフォルダを抽出しました。"

  # GitHubに内容を同期
  GIT_TEMP_DIR="./temp_git_repo"
  rm -rf $GIT_TEMP_DIR
  git clone $GitHubRepository $GIT_TEMP_DIR

  # クローンが成功したかチェック
  if [ ! -d "$GIT_TEMP_DIR" ]; then
    echo "Error: Failed to clone repository $GitHubRepository"
    exit 1
  fi

  cd "$GIT_TEMP_DIR" || { echo "Error: Failed to change directory to $GIT_TEMP_DIR"; exit 1; }

  # 指定されたブランチをチェックアウト
  if git rev-parse --verify $Branch >/dev/null 2>&1; then
    git checkout $Branch
  else
    git checkout -b $Branch
  fi

  # リモートリポジトリの内容を全てクリア
  rm -rf ./*

  # ディレクトリを一度戻してからコピー
  cd ..
  cp -r $TEMP_DIR/* "$GIT_TEMP_DIR/"

  # コピーしたディレクトリに戻る
  cd "$GIT_TEMP_DIR" || { echo "Error: Failed to change directory to $GIT_TEMP_DIR"; exit 1; }

  # 不要な.DS_Storeファイルを削除
  find . -name ".DS_Store" -exec rm -f {} +

  # コミットしてリモートリポジトリにプッシュ
  git add .
  git commit -m "$CONFIG_FILE から指定された内容を同期"
  git push origin $Branch

  cd ..
  rm -rf $GIT_TEMP_DIR

  # 一時ディレクトリを削除
  rm -rf $TEMP_DIR
  echo "$CONFIG_FILE で指定されたリモートリポジトリへの同期が完了しました。"
done

echo "全ての同期が完了しました。"
