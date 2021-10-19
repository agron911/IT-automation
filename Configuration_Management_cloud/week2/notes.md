<<<<<<< HEAD
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
=======
## test
>>>>>>> a965ff4ba81a20f6f5cacab098e8d559186b87ec



### Node
* 定義：
不論是何種系統皆可以執行puppet agent,可以是實體的工作站,伺服器,虛擬機或是
路由器,
只要存在puppet agent而且可以部屬給定的規則,


,因此我們可以部屬基本規則給所有機器,再根據不同機器給予不同的規則.


```
node default {
	class {'sudo':}
	class {'ntp': 
		servers =>['ntp1.example.com','ntp2.example.com']}
}

```
給定特定機器不同的規則

```
node webserver.example.com{
	class { 'sudo': }
	class { 'ntp':
		servers => ['ntp1.example.com','ntp2.example.com]}
	class { 'apache': }
}
```
這個node包含相同的sudo和ntp classes,不過新增了一個apache class.

部署的過程中,puppet會去查看node 的定義,找出符合的node FQDN然後給予那些規則


node definition 通常會被存在於site.pp的檔案中,檔案中定義了哪些classes會被包含在哪些node中


### review 流程
puppet client端重送facts到server,server會處理manifests,產生相對應的catalog,
再傳回給clients 部屬在本地端.

### 安全性
puppet利用公鑰infrastructure or PKI.來建立伺服器和client安全連線.

其中一種作法使用SSL secure sockets layer.

### ssl
私鑰歸特定機器管理,公鑰和其他機器共享.

### 實作

```
sudo puppet config --section master set sutosign true // 設定自動簽核CA,真實情景需要設定成手動

ssh webserver //連線server

sudo apt install puppet  //成功安裝puppet agent, 接下來要和pupper server進行溝通

sudo puppet config set server ubuntu.exmple.com //部屬伺服器

sudo puppet agent -v --test//測試連線狀態
```
假設 我們要架設apache在我們的webserver上
```
~$ vim /etc/puppet/code/enviornment/production/manifests/site.pp

node webserver.example.com {
	class { 'apache': }
}

node default {}

~$ sudo puppet agent -v --test // 這次puppet agent 連線到puppet master並且得到告知它需要安裝且佈置Apache套件.
這包含設定很多不同的服務.
```

上面都是手動測試

#### CTL command
為了自動話一點,首先告訴系統CTL要啟用puppet 服務,由此agent才可以在機器重開機後自己執行

```
~$ sudo systemctl enable puppet
~$ sudo systemctl start puppet

~$ sudo systemctl status puppet // 檢查puppet狀態
```
從此 puppet agent 會有規律性的簡查master 且 請求是否有任何需要部屬到機器上的更新動作.

