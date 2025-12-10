# JY图书管理系统

基于Flask和SQL Server的Web图书管理系统，实现了对图书表的完整CRUD（增删改查）功能。

## 项目特性

- ✅ **完整的CRUD功能**：创建、读取、更新、删除图书记录
- 🎨 **现代化UI设计**：基于Bootstrap 5的响应式界面，支持深色/浅色主题切换
- 🔍 **高级搜索筛选**：实时搜索、多条件筛选、排序功能
- 📊 **数据统计**：统计仪表板、数据可视化图表
- 📥 **数据导入导出**：支持CSV格式的批量导入和导出
- 📄 **分页功能**：支持分页浏览，可自定义每页显示数量
- 🎯 **批量操作**：批量删除、批量选择功能
- 📖 **图书详情**：模态框快速预览、独立详情页、相关图书推荐
- ⚡ **AJAX交互**：异步操作，流畅的用户体验
- ✅ **前后端验证**：确保数据完整性和正确性

## 技术栈

- **后端框架**: Flask 3.0+
- **数据库**: SQL Server
- **数据库驱动**: pymssql 2.2+
- **前端框架**: Bootstrap 5.3.0
- **JavaScript库**: jQuery 3.7.1, Chart.js 4.4.0
- **图标库**: Bootstrap Icons

## 项目结构

```
JY_Book_Manager/
├── app.py                 # Flask主应用文件
├── config.py              # 数据库配置文件
├── requirements.txt       # Python依赖包
├── README.md             # 项目说明文档
├── models/               # 数据模型层
│   ├── __init__.py
│   └── db.py            # 数据库操作类
├── templates/            # HTML模板
│   ├── base.html        # 基础模板
│   ├── index.html       # 图书列表页
│   ├── book_form.html   # 图书表单页（添加/编辑）
│   └── book_detail.html # 图书详情页
└── static/              # 静态资源
    ├── css/
    │   └── style.css    # 自定义样式
    └── js/
        ├── main.js      # 主JavaScript文件
        └── index.js     # 列表页JavaScript
```

## 数据库配置

### 1. 数据库表结构

确保数据库中已创建 `book` 表：

```sql
CREATE TABLE book (
    book_id          CHAR(8)         NOT NULL PRIMARY KEY,
    book_name        NVARCHAR(50)    NOT NULL,
    book_isbn        CHAR(17)        NOT NULL,
    book_author      NVARCHAR(10)    NOT NULL,
    book_publisher   NVARCHAR(50)    NOT NULL,
    book_price       MONEY           NOT NULL,
    interview_times  SMALLINT        NOT NULL
);
```

### 2. 修改配置文件

编辑 `config.py` 文件，修改数据库连接信息：

```python
DB_CONFIG = {
    'server': '你的服务器名称',  # 修改为你的SQL Server服务器名称
    'database': 'JY',              # 数据库名称
    'charset': 'utf8'              # 字符编码
}
```

**服务器名称查找方法：**
- 打开SQL Server Management Studio
- 连接服务器时显示的服务器名称即为所需
- 本地服务器可使用 `localhost` 或 `.`

**注意事项：**
- 系统使用Windows身份验证，无需用户名和密码
- 确保当前Windows用户有访问数据库的权限
- 确保SQL Server服务正在运行

## 安装与运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

按照上述说明修改 `config.py` 文件中的数据库配置。

### 3. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## 主要功能

### 1. 图书列表页
- 卡片视图和表格视图切换
- 实时搜索和多条件筛选
- 分页浏览
- 批量操作
- 数据统计展示

### 2. 添加/编辑图书
- 表单验证
- 字段长度和类型检查
- 实时验证反馈

### 3. 图书详情
- 模态框快速预览
- 独立详情页
- 相关图书推荐（同作者、同出版社）

### 4. 数据管理
- CSV格式导入
- CSV格式导出
- 批量删除

### 5. 高级筛选
- 价格范围筛选
- 借阅次数范围筛选
- 出版社多选筛选
- 作者多选筛选
- 指定字段关键词筛选

## API接口

系统提供RESTful API接口：

- `GET /api/books` - 获取所有图书
- `GET /api/books/<book_id>` - 获取单个图书
- `GET /api/books/paginated` - 分页获取图书
- `POST /api/books` - 创建新图书
- `PUT /api/books/<book_id>` - 更新图书
- `DELETE /api/books/<book_id>` - 删除图书
- `DELETE /api/books/batch` - 批量删除图书
- `GET /api/statistics` - 获取统计数据
- `GET /api/filter/options` - 获取筛选选项
- `POST /api/books/filter` - 高级筛选
- `GET /api/export/csv` - 导出CSV
- `POST /api/import/csv` - 导入CSV

## 使用说明

1. **查看图书列表**：访问首页查看所有图书
2. **搜索图书**：使用搜索框或高级筛选功能
3. **添加图书**：点击"添加图书"按钮，填写表单
4. **编辑图书**：点击编辑按钮修改信息
5. **查看详情**：点击图书名称查看详细信息
6. **删除图书**：点击删除按钮，确认后删除
7. **批量操作**：勾选多本图书进行批量删除
8. **导入数据**：点击"导入"按钮上传CSV文件
9. **导出数据**：点击"导出"按钮下载CSV文件

## 注意事项

1. 确保SQL Server服务正在运行
2. 确保数据库 `JY` 和表 `book` 已创建
3. 确保当前Windows用户有数据库访问权限
4. 图书ID在创建后不可修改
5. 删除操作不可恢复，请谨慎操作
6. CSV导入文件格式需与导出格式一致

## 开发环境

- Python 3.7+
- Flask 3.0+
- SQL Server（支持Windows身份验证）
- pymssql 2.2+

---

