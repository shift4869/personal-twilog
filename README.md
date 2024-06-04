# personal-twilog

<!--![Coverage reports](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/shift4869/ad61760f15c4a67a5c421cf479e3c7e7/raw/02_NNMM.json)-->

## 概要
個人用ツイログ  
特定のアカウントのツイート等を記録する


## 特徴（できること）
- 機能
    - 特定のアカウントのツイートをDBに記録
    - 特定のアカウントのいいね（Likes）をDBに記録
    - 特定のアカウントのTL上に現れたメディア情報をDBに記録
    - 特定のアカウントのTL上に現れた外部リンク情報をDBに記録
    - 特定のアカウントの統計情報（ツイート数、FF数など）をDBに記録
    - ツイッター公式のフルアーカイブjsを取り込み、テーブルとしてDBに保存する機能


## 前提として必要なもの
- Pythonの実行環境(3.11以上)


## 使い方
1. `config/config_example.json` を開き、 `authorize` 項目を設定する
    - ブラウザでログイン済のアカウントについて、以下の値をクッキーから取得
        - ct0 (クッキー中)
        - auth_token (クッキー中)
        - screen_name(上記ct0, auth_tokenに紐づく@マーク抜きのscreen_name)
    - ブラウザ上でのクッキーの確認方法
        - 各ブラウザによって異なるが、概ね `F12を押す→ページ更新→アプリケーションタブ→クッキー` で確認可能
    - 詳しくは「twitter クッキー ct0 auth_token」等で検索
1. `target` 項目に収集対象のアカウントscreen_nameを設定する
    - `status` はenableで収集対象に含める、disableで収集対象としない
1. `config/config_example.json` をリネームし、 `config/config.json` として配置
1. `python ./src/personal_twilog/main.py` で起動
1. 出力された `timeline.db` をsqliteビュワーで開いて確認


## フルアーカイブjsの取り込みについて
1. twitter->設定とプライバシー->「データのアーカイブをダウンロード」を選択
1. パスワード認証を求められるので入力->「アーカイブをリクエスト」を選択
1. ダウンロードの準備が始まるので、1日ほど待つ
1. ダウンロードの準備が完了した連絡がきたらダウンロードする
1. ダウンロードしたzipを解凍し、適当な場所に展開しておく
1. `src/personal_twilog/load_twitter_archive.py` を開く
1. `__main__` 部分にある `input_base_path` に展開した場所のパス、 `output_db_path` にテーブル追加するDBのパスを記載する
1. `python ./src/personal_twilog/load_twitter_archive.py` で起動


## License/Author
[MIT License](https://github.com/shift4869/personal-twilog/blob/master/LICENSE)  
Copyright (c) 2021 - 2024 [shift](https://twitter.com/_shift4869)  


