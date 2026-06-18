# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock
import os
import sys

# Add workspace path to import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pymongo globally
mock_pymongo = MagicMock()
mock_client = MagicMock()
mock_db = MagicMock()
mock_collection = MagicMock()

mock_pymongo.MongoClient.return_value = mock_client
mock_client.__getitem__.return_value = mock_db
mock_db.__getitem__.return_value = mock_collection
mock_pymongo.uri_parser.parse_uri.return_value = {"database": "giao_trinh_ai"}

# Backup original pymongo if exists
orig_pymongo = sys.modules.get("pymongo")

sys.modules["pymongo"] = mock_pymongo
mock_pymongo.ReturnDocument.AFTER = "AFTER"

from mongosql_compat import MongoSQLAlchemy

# Create local instance
db = MongoSQLAlchemy()

# Define test models
class TestUser(db.Model):
    __tablename__ = 'test_user'
    id = db.Column(db.Integer, primary_key=True)
    ten_dang_nhap = db.Column(db.String(150), nullable=False)
    mat_khau_hash = db.Column(db.String(255), nullable=False)
    la_admin = db.Column(db.Boolean, default=False)

class TestPost(db.Model):
    __tablename__ = 'test_post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('test_user.id'))
    user = db.relationship('TestUser', backref='posts')

class TestMongoDBCompat(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        # Restore original pymongo to be a good citizen
        if orig_pymongo:
            sys.modules["pymongo"] = orig_pymongo
        else:
            sys.modules.pop("pymongo", None)

    def setUp(self):
        MongoSQLAlchemy._client = mock_client
        MongoSQLAlchemy._db_name = "giao_trinh_ai"
        mock_collection.reset_mock()
        mock_db["counters"].reset_mock()

    def test_model_serialization(self):
        # Test TestUser attribute-to-db mapping
        user = TestUser(ten_dang_nhap="testuser", mat_khau_hash="password_hash", la_admin=True)
        user.id = 42
        
        data = user._to_dict()
        self.assertEqual(data["_id"], 42)
        self.assertEqual(data["ten_dang_nhap"], "testuser")
        self.assertEqual(data["mat_khau_hash"], "password_hash")
        self.assertEqual(data["la_admin"], True)
        
        # Test deserialization
        loaded = TestUser._from_dict({
            "_id": 42,
            "ten_dang_nhap": "testuser",
            "mat_khau_hash": "password_hash",
            "la_admin": True
        })
        self.assertEqual(loaded.id, 42)
        self.assertEqual(loaded.ten_dang_nhap, "testuser")
        self.assertEqual(loaded.mat_khau_hash, "password_hash")
        self.assertEqual(loaded.la_admin, True)

    def test_query_filtering_and_sorting(self):
        # Test filter_by translating attribute names to DB column names
        query = TestUser.query.filter_by(ten_dang_nhap="admin", mat_khau_hash="pw")
        self.assertEqual(query.filters["ten_dang_nhap"], "admin")
        self.assertEqual(query.filters["mat_khau_hash"], "pw")
        
        # Test filter with contains, ==, and >
        q1 = TestUser.query.filter(TestUser.ten_dang_nhap.contains("adm"))
        self.assertEqual(q1.filters["ten_dang_nhap"]["$regex"], "adm")
        
        q2 = TestUser.query.filter(TestUser.id == 42)
        self.assertEqual(q2.filters["_id"], 42)
        
        q3 = TestUser.query.filter(TestUser.id > 10)
        self.assertEqual(q3.filters["_id"]["$gt"], 10)
        
        # Test boolean coercion
        q_bool1 = TestUser.query.filter_by(la_admin=True)
        self.assertEqual(q_bool1.filters["la_admin"], {"$in": [True, 1]})
        
        q_bool2 = TestUser.query.filter(TestUser.la_admin == False)
        self.assertEqual(q_bool2.filters["la_admin"], {"$in": [False, 0]})
        
        # Test integer coercion
        q_int1 = TestUser.query.filter_by(id="123")
        self.assertEqual(q_int1.filters["_id"], 123)
        
        q_int2 = TestUser.query.filter(TestUser.id == "456")
        self.assertEqual(q_int2.filters["_id"], 456)
        
        # Test order_by translating attributes to sort fields
        sorted_query = query.order_by(TestUser.id.desc())
        self.assertEqual(sorted_query.sort_fields, [("_id", -1)])

    def test_session_commit_insert_and_update(self):
        # Mock the counter increment for new IDs
        mock_db["counters"].find_one_and_update.return_value = {"seq": 99}
        
        # Add new user (without ID)
        user = TestUser(ten_dang_nhap="newuser")
        db.session.add(user)
        
        db.session.commit()
        
        # Verify counter was fetched
        mock_db["counters"].find_one_and_update.assert_called_once_with(
            {"_id": "test_user"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=mock_pymongo.ReturnDocument.AFTER
        )
        
        # Verify insert occurred
        self.assertEqual(user.id, 99)
        mock_db["test_user"].replace_one.assert_called_once()
        call_args = mock_db["test_user"].replace_one.call_args[0]
        self.assertEqual(call_args[0], {"_id": 99})
        self.assertEqual(call_args[1]["ten_dang_nhap"], "newuser")
        
        # Reset mock
        mock_db["test_user"].replace_one.reset_mock()
        
        # Test update of tracked/loaded instance
        mock_db["test_user"].find_one.return_value = {"_id": 100, "ten_dang_nhap": "trackeduser", "la_admin": False}
        loaded_user = TestUser.query.get(100)
        self.assertEqual(loaded_user.ten_dang_nhap, "trackeduser")
        
        # Mutate
        loaded_user.la_admin = True
        db.session.commit()
        
        # Verify update was saved
        mock_db["test_user"].replace_one.assert_called_once()
        update_call = mock_db["test_user"].replace_one.call_args[0]
        self.assertEqual(update_call[0], {"_id": 100})
        self.assertEqual(update_call[1]["la_admin"], True)

    def test_session_commit_delete(self):
        # Create user with ID
        user = TestUser(ten_dang_nhap="todelete")
        user.id = 50
        
        db.session.delete(user)
        db.session.commit()
        
        # Verify delete was called
        mock_db["test_user"].delete_one.assert_called_once_with({"_id": 50})

    def test_get_or_404(self):
        from werkzeug.exceptions import NotFound
        
        # Test found
        mock_db["test_user"].find_one.return_value = {"_id": 42, "ten_dang_nhap": "someuser"}
        res = TestUser.query.get_or_404(42)
        self.assertEqual(res.id, 42)
        
        # Test not found
        mock_db["test_user"].find_one.return_value = None
        with self.assertRaises(NotFound):
            TestUser.query.get_or_404(999)
            
        # Test db.get_or_404 found
        mock_db["test_user"].find_one.return_value = {"_id": 42, "ten_dang_nhap": "someuser"}
        res2 = db.get_or_404(TestUser, 42)
        self.assertEqual(res2.id, 42)

    def test_identity_map_and_session_cleanup(self):
        # Reset session state
        db.session.remove()
        self.assertEqual(len(db.session._tracked), 0)
        
        # Load user once
        mock_db["test_user"].find_one.return_value = {"_id": 42, "ten_dang_nhap": "someuser", "la_admin": False}
        user1 = TestUser.query.get(42)
        self.assertEqual(len(db.session._tracked), 1)
        self.assertIn(user1, db.session._tracked)
        
        # Load user again - must return the same instance and update properties
        mock_db["test_user"].find_one.return_value = {"_id": 42, "ten_dang_nhap": "someuser", "la_admin": True}
        user2 = TestUser.query.get(42)
        
        # Verify identity map (same instance)
        self.assertIs(user1, user2)
        self.assertEqual(len(db.session._tracked), 1)
        self.assertEqual(user1.la_admin, True)
        
        # Verify remove cleanup
        db.session.remove()
        self.assertEqual(len(db.session._tracked), 0)

if __name__ == "__main__":
    unittest.main()
