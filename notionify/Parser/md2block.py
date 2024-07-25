from mistletoe.block_token import BlockToken, tokenize
import itertools
from mistletoe import span_token
from md2notion.NotionPyRenderer import NotionPyRenderer


class Document(BlockToken):
    """
    Document token.
    """
    def __init__(self, lines):
        if isinstance(lines, str):lines = lines.splitlines(keepends=True)
        lines = [line if line.endswith('\n') else '{}\n'.format(line) for line in lines]

        # add new line above and below '$$\n'
        new_lines = []
        temp_line = None
        triggered = False
        for line in lines:
            #if line.strip().replace('\n',"") =='':continue
            if not triggered and '$$\n' in line:
                temp_line = [None, line, None]
                triggered = True
            elif triggered:
                temp_line[1] += line
                if '$$\n' in line:
                    temp_line[2] = '\n'
                    new_lines.append(temp_line)
                    temp_line = None
                    triggered = False
                    
            else:
                new_lines.append([None, line, None])

        if temp_line is not None:
            new_lines.append(temp_line)
        
        
        new_lines = list(itertools.chain(*new_lines))
        new_lines = list(filter(lambda x: x is not None, new_lines))
        new_lines = ''.join(new_lines)
        lines = new_lines.splitlines(keepends=True)
        lines = [line if line.endswith('\n') else '{}\n'.format(line) for line in lines]
        #lines = [[t[1]] for  t in new_lines]
        
        
        self.footnotes = {}
        global _root_node
        _root_node = self
        span_token._root_node = self
        self.children = tokenize(lines)
        span_token._root_node = None
        _root_node = None


def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as mdFile:
        with NotionPyRenderer() as renderer:
            a  = Document(mdFile)
            out= renderer.render(a)
    return out


def read_file_content(content):
    with NotionPyRenderer() as renderer:
        a  = Document(content)
        out= renderer.render(a)
    return out


if __name__ == '__main__':
    for block in read_file("test.md"):
        print(block)