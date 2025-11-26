# Edge Cases Test Document

This document contains various edge cases for testing.

## Empty Sections

## Single Word

Word.

## No Punctuation Section

word word word word word word word

## Code Only Section

```python
def hello():
    print("world")
    return True
```

```javascript
console.log('test');
```

## Heading Hierarchy Issues

#### H4 Before H2

## H2 After H4

# H1 in Middle

### H3 Without H2

## Unicode and Special Characters

Hello 世界 🌍 🚀 Привет мир مرحبا

## Excessive Formatting

**bold** _italic_ **bold** _italic_ **bold** _italic_ **bold** _italic_ **bold** _italic_ **bold** _italic_ **bold** _italic_ **bold** _italic_ **bold** _italic_ **bold** _italic_

## Very Long Sentence

This is an extremely long sentence that just keeps going and going without any real purpose other than to test how the analyzer handles sentences that are unnecessarily verbose and contain way too many words and clauses and phrases that really should have been broken up into multiple shorter sentences for better readability but instead continue to ramble on and on making the reader wonder when it will ever end.

## Single Character

X

## Numbers Only

1 2 3 4 5 6 7 8 9 10 11 12 13 14 15

## Repeated Words

The the the the the the the the the.

## List Mayhem

- Item
  - Nested
    - Double nested
      - Triple nested
        - Quadruple nested
          - Quintuple nested

1. One
2. Two

- Suddenly unordered

3. Back to ordered?

## Malformed Markdown

\*\*bold without close

\*italic without close

[link without close

## Empty Lines

## Tab Characters

    Indented with tab
    	Double tab
    		Triple tab
