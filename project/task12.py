from antlr4 import InputStream, CommonTokenStream

from project.lang.langLexer import langLexer
from project.lang.langParser import langParser

from project.tc import TypeCheckVisitor, TypeContext
from project.interpreter import InterpreterVisitor


def typing_program(program: str) -> bool:
    input_stream = InputStream(program)
    lexer = langLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = langParser(stream)
    tree = parser.prog()

    visitor = TypeCheckVisitor()
    try:
        visitor.visit(tree)
        return True
    except Exception as e:
        print(e)
        return False


"""
def exec_program(program: str) -> dict[str, set[tuple]]:
    input_stream = InputStream(program)
    lexer = langLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = langParser(stream)
    tree = parser.prog()

    visitor = TypeCheckVisitor()
    context: TypeContext = visitor.visit(tree)

    interpreterVisitor = InterpreterVisitor(context)
    return interpreterVisitor.visit(tree)
"""
