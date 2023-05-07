import understand
import csv

def getCsvByfilePath(udb_path,file_path):
    filename='j'+"".join(file_path)
    db = understand.open(udb_path)
    file = db.lookup_uniquename(filename)
    result = []
    lexer=file.lexer(False, 8, False, True)
    lexeme = lexer.first()
    while lexeme:
        
        result.append([lexeme.text(), lexeme.token()])
        lexeme = lexeme.next()
    
    with open(filename[1:] + ".csv", "w", encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(result)
    db.close()