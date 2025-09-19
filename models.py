from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -------------------------------------------------
# 🔧 Modelo Material
# -------------------------------------------------
class Material(db.Model):
    __tablename__ = "materiais"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco_material = db.Column(db.Float, default=0.0)   # €/ton
    preco_transporte = db.Column(db.Float, default=0.0) # €/ton

    def __repr__(self):
        return f"<Material {self.nome}>"


# -------------------------------------------------
# 🔧 Modelo Mistura
# -------------------------------------------------
class Mistura(db.Model):
    __tablename__ = "misturas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    baridade = db.Column(db.Float, nullable=False)

    composicoes = db.relationship("Composicao", backref="mistura", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Mistura {self.nome}>"


# -------------------------------------------------
# 🔧 Modelo Composição
# -------------------------------------------------
class Composicao(db.Model):
    __tablename__ = "composicoes"

    id = db.Column(db.Integer, primary_key=True)
    mistura_id = db.Column(db.Integer, db.ForeignKey("misturas.id"), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey("materiais.id"), nullable=False)
    percentagem = db.Column(db.Float, nullable=False)  # %

    material = db.relationship("Material")

    def __repr__(self):
        return f"<Composicao Mistura={self.mistura_id} Material={self.material_id} {self.percentagem}%>"
