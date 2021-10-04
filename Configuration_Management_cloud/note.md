## Configuration Managemennt
#### System nowadays
Tools can be used to manage locally hosted infrastructure, like bare machine,work station...
* Puppet (focus on this)
* Chef
* CFEngine
* Ansible

當我們在使用configuration management system時，寫下電腦需要以何種規則佈署，這些規則會被自動執行，這表示我們可以利用可自動化工具處裡的檔案模型化IT infra 的行為。 而這些檔案可以在 version control system 中追蹤。

如果infra中的所有細節資訊都正當的存儲在系統中，可以快速部署新設備當任何系統崩潰產生。

IaC (Infrastructure aas Code) 的主軸時常在雲計算的環境中使用，這些機器被當作是內部可改變資源而非獨立電腦。

而當我們使用IaC的技術，這些configuration的資訊都會被存在一個檔案之中，而這些檔案皆可以被VCS系統所處裡。不僅如此，可以很清楚地部記錄每次的變更，不同的版本，也能輕鬆的恢復到希望的版本。在測試的過程中，這樣的設計也會有輕便且安全性高。

* Consistent
* Versioned
* Reliable
* Repeatable

### Puppet
* Cross-platform
使用client-server架構，client:puppet agent, server:puppet master.agent會傳送大量包含電腦的資料給master,mseter處理這些資料，產生規則傳回給agent執行。

```
class sudo {
    package { 'sudo':
        ensure => present,
    }
}
```
這個package sudo 應該要在每一台電腦上出現一旦這個規則被採用，當這個規則被採用會自動下載package。

### Puppet facts
Variables that represent the characteristics of the system
當puppet agent開始執行，會呼叫一個名為factor的程式，factor會分析目前的系統，並且儲存所有從facts中取得的資訊。完成之後，傳送這些facts的值到puppet server，計算出那些規則需要被執行

```
if $facts['is_virtual']{
    package { 'smartmontools' :
        ensure => purged,
    }
}else{
    package {' smartmontools' :
        ensure => install    
    }
}
```

Puppet使用的是
