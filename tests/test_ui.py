"""
Unit tests for UI session management and flash notifications.
"""

import pytest
import streamlit as st
from src.ui_common import set_flash_message, render_flash_messages, init_session_state


def test_flash_message_lifecycle():
    # Test setting a flash message
    test_msg = "Optimization executed successfully!"
    set_flash_message(test_msg, level="success", icon="🚀")

    assert "_flash_message" in st.session_state
    assert st.session_state["_flash_message"]["message"] == test_msg
    assert st.session_state["_flash_message"]["level"] == "success"
    assert st.session_state["_flash_message"]["icon"] == "🚀"

    # Test rendering and consumption
    render_flash_messages()
    assert "_flash_message" not in st.session_state


def test_init_session_state():
    init_session_state()
    assert "simulator" in st.session_state
    assert "predictor" in st.session_state
    assert "pipeline" in st.session_state
    assert "latest_result" in st.session_state
    assert "comparator" in st.session_state
    assert "exp_manager" in st.session_state
