import pytest
import book
import user
import library
import main


# =====================================================================
# TEMA 7 - FIXTURES
# El libro "Orgullo y prejuicio" y el usuario Tenoch se repetían en
# varias pruebas. Los creo una sola vez aquí y cada prueba los pide
# como argumento. Cada prueba recibe una copia nueva.
# =====================================================================
@pytest.fixture
def libro():
    return book.Book("Orgullo y prejuicio", "Tenoch M", 2026, "ISBN0001")


@pytest.fixture
def lib_init():
    lib = library.Library()
    lib.add_book(book.Book("Orgullo y prejuicio", "Tenoch M", 2026, "ISBN0001"))
    lib.add_user(user.User("Tenoch", "0001"))
    return lib


# Texto que main.run() imprime cada vez que muestra el menú
MENU = (
    "\n--- Library System ---\n"
    "1. Borrow a book\n"
    "2. Return a book\n"
    "3. View user history\n"
    "0. Exit\n"
)


# =====================================================================
# Pruebas básicas de Book (usan la fixture "libro")
# =====================================================================
@pytest.mark.unit
def test_borrow_book(libro):
    assert libro.title == "Orgullo y prejuicio"
    libro.borrow()
    assert libro.borrowed == True


@pytest.mark.unit
def test_return_book(libro):
    libro.borrow()
    libro.return_book()
    assert libro.borrowed == False


# =====================================================================
# TEMA 9 - pytest.raises()
# Entrada inválida: prestar un libro que ya está prestado.
# Debe generar ValueError con ese mensaje.
# =====================================================================
@pytest.mark.unit
def test_borrow_two_times_book(libro):
    libro.borrow()
    with pytest.raises(ValueError, match="The book is already borrowed"):
        libro.borrow()


# =====================================================================
# TEMAS 4 y 5 - pytest.ini y MARCADORES
# "prestamos" es un marcador personalizado registrado en pytest.ini.
#   Ejecutar solo esta prueba:   pytest -m prestamos
# "wip" está en la otra prueba.  Ejecutar:  pytest -m wip
# =====================================================================
@pytest.mark.prestamos
def test_library_borrow(lib_init):
    lib_init.borrow_book("0001", "ISBN0001")
    assert lib_init.books[0].borrowed == True
    assert len(lib_init.users[0].get_history()) == 1


@pytest.mark.wip
def test_library_user_not_registered(lib_init):
    with pytest.raises(ValueError, match="User not found"):
        lib_init.borrow_book("0002", "ISBN0001")


# =====================================================================
# TEMA 1 - monkeypatch.setattr()
# Sustituyo temporalmente el atributo "borrowed" del libro por True,
# como si otra persona ya lo hubiera pedido. El préstamo debe fallar.
# =====================================================================
@pytest.mark.unit
def test_monkeypatch_setattr(lib_init, monkeypatch):
    monkeypatch.setattr(lib_init.books[0], "borrowed", True)
    with pytest.raises(ValueError, match="The book is already borrowed"):
        lib_init.borrow_book("0001", "ISBN0001")


# =====================================================================
# TEMA 2 - monkeypatch.delattr()
# Elimino temporalmente el método register_borrow de la clase User.
# borrow_book lo usa, así que debe fallar con AttributeError.
# =====================================================================
@pytest.mark.unit
def test_monkeypatch_delattr(lib_init, monkeypatch):
    monkeypatch.delattr(user.User, "register_borrow")
    with pytest.raises(AttributeError):
        lib_init.borrow_book("0001", "ISBN0001")


# =====================================================================
# TEMA 3 - monkeypatch.setitem()
# Cambio temporalmente settings["loans_enabled"] a False.
# borrow_book debe usar el nuevo valor: NO presta e imprime un aviso.
# =====================================================================
@pytest.mark.unit
def test_monkeypatch_setitem(lib_init, monkeypatch, capsys):
    monkeypatch.setitem(library.settings, "loans_enabled", False)

    lib_init.borrow_book("0001", "ISBN0001")

    assert lib_init.books[0].borrowed == False
    captured = capsys.readouterr()
    assert captured.out == "Loans are disabled\n"


# =====================================================================
# TEMA 6 - PARAMETRIZE
# Una sola función de prueba, tres entradas distintas con su
# resultado esperado (el mensaje del error).
# =====================================================================
@pytest.mark.unit
@pytest.mark.parametrize("user_id, isbn, mensaje_esperado", [
    ("0002", "ISBN0001", "User not found"),   # usuario no existe
    ("0001", "ISBN9999", "Book not found"),   # libro no existe
    ("9999", "ISBN9999", "User not found"),   # ninguno existe: busca primero al usuario
])
def test_borrow_parametrize(lib_init, user_id, isbn, mensaje_esperado):
    with pytest.raises(ValueError, match=mensaje_esperado):
        lib_init.borrow_book(user_id, isbn)


# =====================================================================
# TEMA 8 - COBERTURA DE CAJA BLANCA
#   pytest --cov=library --cov-report=term-missing
# Sin esta prueba, el reporte marcaba en "Missing" las líneas de
# Library.return_book(), porque ninguna prueba devolvía un libro
# desde la biblioteca. Esta prueba ejecuta ese camino.
# =====================================================================
@pytest.mark.unit
def test_library_return_book(lib_init):
    lib_init.borrow_book("0001", "ISBN0001")
    lib_init.return_book("0001", "ISBN0001")
    assert lib_init.books[0].borrowed == False
    assert len(lib_init.users[0].get_history()) == 2


# =====================================================================
# TEMA 10 - try-except
# A) Excepción que se PROPAGA: Library.borrow_book NO tiene try-except,
#    así que el error sube hasta la prueba y aquí lo atrapo.
# B) Excepción CAPTURADA: main.run() SÍ tiene try-except. El programa
#    no truena: imprime "Error: ..." y sigue funcionando.
# =====================================================================
@pytest.mark.unit
def test_excepcion_se_propaga(lib_init):
    lib_init.borrow_book("0001", "ISBN0001")
    try:
        lib_init.borrow_book("0001", "ISBN0001")
        assert False, "Debió lanzar ValueError"
    except ValueError as e:
        assert str(e) == "The book is already borrowed"


@pytest.mark.unit
def test_excepcion_capturada(monkeypatch, capsys):
    # Lo que "escribe" el usuario: opción 3, un ID que no existe, salir
    respuestas = iter(["3", "U999", "0"])
    monkeypatch.setattr("builtins.input", lambda mensaje: next(respuestas))

    main.run()   # no truena aunque haya error, porque main lo captura

    captured = capsys.readouterr()
    assert "Error: User not found" in captured.out


# =====================================================================
# TEMA 11 - capsys
# Elijo una opción inválida ("9") y luego salgo ("0").
# Verifico el texto EXACTO que se imprimió.
# =====================================================================
@pytest.mark.unit
def test_capsys(monkeypatch, capsys):
    respuestas = iter(["9", "0"])
    monkeypatch.setattr("builtins.input", lambda mensaje: next(respuestas))

    main.run()

    captured = capsys.readouterr()
    assert captured.out == MENU + "Invalid option\n" + MENU


