# 直播通知

* 目前來源支援
    * holodex: 會自動偵測新影片
    * youtube: 需手動新增新影片

## 相關的指令

``` bash
[p]stream 設置直播相關的
[p]stream collab 設置聯動相關的
[p]member 設置成員相關的
[p]channel 設置頻道相關的
[p]starsset message 送出訊息的格式
```

* 備註
  * `guild_collab_stream`、`guild_stream`、`stream_id`: 都是輸入待機台的 ID

## 加入要關注的頻道

``` bash
[p]member add [成員名稱] [來源] [頻道 ID]
[p]member set all [成員名稱] [通知頻道] [聊天頻道] [會員頻道] [紅色值] [綠色值] [藍色值] [emoji]
```

例子

``` bash
[p]member add izuru holodex UCZgOv3YDEs-ZnZWDYVwJdmA
[p]member set all izuru #通知 #聊天 #會員 70 0 255 🎸
```

## 聯動加入方式

1. 直接創一個 (推薦用於已知聯動時間但待機台還沒全部開完)

    ``` bash
    [p]stream collab create [時間] [討論頻道] [多個聯動成員的名字]
    ```

    例如

    ``` bash
    [p]stream collab create 2022/07/27T11:00 861602293761835008 miyabi,temma,arurandeisu
    ```

    或

    ``` bash
    [p]stream collab create 2022/07/27T11:00 861602293761835008
    ```
    + 選擇表符

2. 將多個直播建立成聯動 (推薦用於待機台開完的情況下)

    ``` bash
    [p]stream collab add [多個直播 ID] [討論頻道]
    ```

    例如

    ``` bash
    [p]create 2022/07/27T11:00 861602293761835008 yPElRWsqxQg,Rfk5LAfp7L8
    ```

3. 將`成員`或`直播`加到另一個直播 (推薦用於已開台、更改設定時使用 或 討論頻道在直播 1 的頻道時使用)

    * 加入**直播**

    ``` bash
    [p]stream collab add_stream [直播1] [直播2]
    ```

    例如

    ``` bash
    [p]stream collab add_stream yPElRWsqxQg Rfk5LAfp7L8
    ```

    * 加入**成員**
    
    ``` bash
    [p]stream collab add_stream [直播1] [成員名稱]
    ```

    例如

    ``` bash
    [p]stream collab add_stream yPElRWsqxQg astel
    ```
