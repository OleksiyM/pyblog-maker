# PyBlogMaker

PyBlogMaker is a powerful static blog generator that transforms Markdown files into a fully-featured blog website. It offers comprehensive support for categories, tags, SEO optimization, and modern web features out of the box.

## Features

- **Advanced Markdown Support**: Create content using Markdown with support for code blocks, tables, and images
- **Smart Content Organization**: Built-in category and tag system for better content structure
- **Modern Theme System**: Responsive and customizable themes with mobile-first design
- **SEO Ready**: Automatic generation of sitemap.xml, robots.txt, and meta tags
- **Content Syndication**: Built-in RSS and Atom feeds for content distribution
- **Developer Friendly**: Syntax highlighting for over 100 programming languages
- **Analytics Integration**: Easy Google Analytics setup for tracking visitors
- **Smart Pagination**: Automatic content pagination for better performance
- **Build Tools**: Detailed build reports and automatic ZIP archives for deployment

## Installation

```bash
git clone https://github.com/yourusername/pyblog-maker.git
cd pyblog-maker
pip install -r requirements.txt
```

## Usage

1. Create a new blog:
```bash
python src/bloggen.py -n my-blog-name
```

**Note** Automatic blog creation not working for now, you have to do it manually. Also you need to create theme manually too.

2. Add your posts in Markdown format to the `posts` directory with required metadata:
```markdown
Title: Your Post Title
date: YYYY-MM-DD
Description: Your post description
Keywords: keyword1, keyword2, keyword3
Categories: Category1, Category2
Image: your-post-image.jpg
Tags: tag1, tag2
Author: Your Name
Draft: true|false

Your content here...
```

3. Customize the theme in the `templates` directory

4. Build your blog:
```bash
python src/bloggen.py -n my-blog-name -t default
```

The generated blog will be available in the `my-blog-name/dist` directory.

## Roadmap

### Core Features
- [ ] Full GitHub Markdown format support
  - Tables with alignment
  - Task lists
  - Footnotes
  - Emoji support
  - Auto-linking references
- [ ] YAML configuration for blogs
  - Global blog settings
  - Theme configuration
  - Build options
  - Custom plugins support
- [ ] Automatic blog creation with default theme
  - Scaffolding tool for new blogs
  - Sample content generation
  - Configuration wizard

### Theme Improvements
- [ ] Enhanced default theme
  - Modern, minimalist design
  - Dark mode support
  - Improved typography
  - Better mobile experience
- [ ] Theme development tools
  - Theme hot-reloading
  - Theme documentation
  - Component library

### Performance Optimizations
- [ ] Asset minification
  - CSS/JS minification
  - HTML compression
  - Selective bundling
- [ ] Image optimization
  - Automatic image compression
  - Responsive images
  - WebP conversion
  - Lazy loading

### Future Enhancements
- [ ] Multi-language support
- [ ] Comment system integration
- [ ] Search functionality
- [ ] Social media integration
- [ ] Custom shortcodes
- [ ] Draft preview system
- [ ] Incremental builds
- [ ] Plugin system

## License

This project is licensed under the [MIT License](LICENSE).