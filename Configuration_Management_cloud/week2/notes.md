### 安裝puppet

```
sudo apt install puppet-master
```

假設要使用Puppet來確保一些好使用的工具來進行除錯,
首先我們要將規則儲存起來,這些檔案稱manifest檔.pp.

```
package { ' htop':
	ensure =>present,
}
```

通常puppet manifest ,裡面包含著非常多的resources並且和其他的皆有相關,
查看其中一個例子 ntp.pp

裡面我們有宣告一些他們之間的關係,配置需求文件包含著Package['ntp'],service需要配置文件

,由此puppet知道在開始啟動服務之前,配置文件必須先正確的設定,而配置文件之前,package必須先安裝.
配置

#### 不同管理事件
在任何配置管理部屬系統上,有很多不同事件可被管理,
* 下載一些套件
* 複製一些配置部屬文件
* 開啟服務
* 排程一些週期性的工作
* 確保使用者和群組有創建,特定設備的權限,或是存取一些特定設備執行一些未提供的指令

也可以根據不同的設備決定不同的部屬條件,ex:工作站和一般電腦所需的配置文件就不同

### 模組 Module
* manifest和相關資料的集合


* 啟用apache

```
sudo apt install puppet-module-puppetlabs-apache
```
