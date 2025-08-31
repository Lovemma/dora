/// Segmenter for streaming text that intelligently buffers chunks into meaningful segments.
/// 
/// The segmenter is designed for real-time text-to-speech applications where sending
/// individual characters or words would overwhelm the TTS system. It buffers incoming
/// text chunks and emits complete segments based on punctuation boundaries.
/// 
/// # Example
/// ```
/// let mut segmenter = StreamSegmenter::new(10);
/// assert_eq!(segmenter.add_chunk("Hello"), None);
/// assert_eq!(segmenter.add_chunk(" world."), Some("Hello world.".to_string()));
/// ```
pub struct StreamSegmenter {
    buffer: String,
    word_count: usize,
    max_words_without_punctuation: usize,
}

impl StreamSegmenter {
    pub fn new(max_words: usize) -> Self {
        Self {
            buffer: String::new(),
            word_count: 0,
            max_words_without_punctuation: max_words,
        }
    }

    /// Add a text chunk to the buffer and return a segment if one is ready.
    /// 
    /// The method buffers the incoming chunk and checks if a meaningful segment
    /// can be emitted based on punctuation marks or word count limits.
    /// 
    /// # Arguments
    /// * `chunk` - A text chunk received from the streaming API
    /// 
    /// # Returns
    /// * `Some(String)` - A complete segment ready for TTS processing
    /// * `None` - No segment ready yet, more buffering needed
    pub fn add_chunk(&mut self, chunk: &str) -> Option<String> {
        self.buffer.push_str(chunk);
        
        // Count words in the current buffer
        self.word_count = self.buffer.split_whitespace().count();
        
        // Check if we should emit a segment
        if self.should_emit_segment() {
            self.emit_segment()
        } else {
            None
        }
    }
    
    /// Check if we should emit a segment
    fn should_emit_segment(&self) -> bool {
        if self.buffer.is_empty() {
            return false;
        }
        
        // Check for meaningful punctuation (Chinese and English)
        let punctuation_marks = [
            '。', '！', '？', '；', '：',  // Chinese
            '.', '!', '?', ';', ':',       // English
            '，', ',',                      // Comma (both Chinese and English)
            '\n',                           // Newline
        ];
        
        // Check if buffer ends with punctuation
        let has_punctuation = self.buffer.chars().any(|c| punctuation_marks.contains(&c));
        
        // Emit if:
        // 1. We have punctuation, OR
        // 2. We have reached max words without punctuation
        has_punctuation || self.word_count >= self.max_words_without_punctuation
    }
    
    /// Emit the current buffer as a segment
    fn emit_segment(&mut self) -> Option<String> {
        if self.buffer.is_empty() {
            return None;
        }
        
        // Find the best split point
        let split_point = self.find_split_point();
        
        if split_point > 0 {
            // Take the segment up to the split point
            let segment = self.buffer[..split_point].to_string();
            
            // Keep the rest in the buffer
            self.buffer = self.buffer[split_point..].trim_start().to_string();
            self.word_count = self.buffer.split_whitespace().count();
            
            Some(segment)
        } else if self.word_count >= self.max_words_without_punctuation {
            // No punctuation found but we've reached max words
            // Emit the entire buffer
            let segment = self.buffer.clone();
            self.buffer.clear();
            self.word_count = 0;
            Some(segment)
        } else {
            None
        }
    }
    
    /// Find the best point to split the buffer
    fn find_split_point(&self) -> usize {
        // Priority punctuation for splitting (sentence endings first)
        let sentence_endings = ['。', '！', '？', '.', '!', '?'];
        let clause_endings = ['；', '：', ';', ':'];
        let soft_breaks = ['，', ',', '\n'];
        
        // Try to find sentence ending first
        if let Some(pos) = self.find_last_punctuation(&sentence_endings) {
            return pos + self.char_len_at(pos);
        }
        
        // Then try clause endings
        if let Some(pos) = self.find_last_punctuation(&clause_endings) {
            return pos + self.char_len_at(pos);
        }
        
        // Finally try soft breaks if we have enough words
        if self.word_count >= 5 {
            if let Some(pos) = self.find_last_punctuation(&soft_breaks) {
                return pos + self.char_len_at(pos);
            }
        }
        
        0
    }
    
    /// Find the last occurrence of any punctuation mark
    fn find_last_punctuation(&self, marks: &[char]) -> Option<usize> {
        self.buffer
            .char_indices()
            .rev()
            .find(|(_, c)| marks.contains(c))
            .map(|(i, _)| i)
    }
    
    /// Get the byte length of the character at the given position
    fn char_len_at(&self, byte_pos: usize) -> usize {
        self.buffer[byte_pos..]
            .chars()
            .next()
            .map(|c| c.len_utf8())
            .unwrap_or(1)
    }
    
    /// Force emit any remaining buffered content.
    /// 
    /// This should be called when the stream ends to ensure no text is lost.
    /// After flushing, the buffer is cleared and ready for new content.
    /// 
    /// # Returns
    /// * `Some(String)` - The remaining buffered text
    /// * `None` - Buffer was already empty
    pub fn flush(&mut self) -> Option<String> {
        if self.buffer.is_empty() {
            None
        } else {
            let segment = self.buffer.clone();
            self.buffer.clear();
            self.word_count = 0;
            Some(segment)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_sentence_segmentation() {
        let mut segmenter = StreamSegmenter::new(10);
        
        // Add chunks
        assert_eq!(segmenter.add_chunk("Hello"), None);
        assert_eq!(segmenter.add_chunk(" world"), None);
        assert_eq!(segmenter.add_chunk("."), Some("Hello world.".to_string()));
        
        assert_eq!(segmenter.add_chunk(" How"), None);
        assert_eq!(segmenter.add_chunk(" are"), None);
        assert_eq!(segmenter.add_chunk(" you?"), Some(" How are you?".to_string()));
    }
    
    #[test]
    fn test_chinese_segmentation() {
        let mut segmenter = StreamSegmenter::new(10);
        
        assert_eq!(segmenter.add_chunk("你好"), None);
        assert_eq!(segmenter.add_chunk("世界"), None);
        assert_eq!(segmenter.add_chunk("。"), Some("你好世界。".to_string()));
        
        assert_eq!(segmenter.add_chunk("今天"), None);
        assert_eq!(segmenter.add_chunk("天气"), None);
        assert_eq!(segmenter.add_chunk("很好"), None);
        assert_eq!(segmenter.add_chunk("！"), Some("今天天气很好！".to_string()));
    }
    
    #[test]
    fn test_max_words() {
        let mut segmenter = StreamSegmenter::new(5);
        
        // Add exactly 5 words - should trigger emission
        assert_eq!(segmenter.add_chunk("one two three four five"), Some("one two three four five".to_string()));
        
        // Test with fewer words than limit
        let mut segmenter2 = StreamSegmenter::new(5);
        assert_eq!(segmenter2.add_chunk("one two three"), None);
        assert_eq!(segmenter2.add_chunk(" four"), None);
        // Adding fifth word triggers emission
        assert_eq!(segmenter2.add_chunk(" five"), Some("one two three four five".to_string()));
    }
    
    #[test]
    fn test_flush() {
        let mut segmenter = StreamSegmenter::new(10);
        
        assert_eq!(segmenter.add_chunk("Hello world"), None);
        assert_eq!(segmenter.flush(), Some("Hello world".to_string()));
        assert_eq!(segmenter.flush(), None); // Nothing left
    }
}