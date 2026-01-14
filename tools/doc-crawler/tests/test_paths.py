"""Tests for semantic path generation."""

from doc_crawler.paths import (
    TOPIC_DESCRIPTIONS,
    TOPIC_KEYWORDS,
    classify_topic,
    extract_keywords,
    generate_semantic_path,
    slugify,
)


class TestSlugify:
    """Tests for slugify function."""

    def test_basic_slugification(self) -> None:
        """Test basic title to slug conversion."""
        assert slugify("How to Create a VLAN") == "how-to-create-a-vlan"
        assert slugify("Simple Title") == "simple-title"

    def test_special_characters_removed(self) -> None:
        """Test that special characters are removed."""
        assert slugify("VLANs & Networks: A Guide") == "vlans-networks-a-guide"
        assert slugify("What's New in 8.0?") == "whats-new-in-80"
        assert slugify("Setup (Quick Start)") == "setup-quick-start"

    def test_whitespace_handling(self) -> None:
        """Test that various whitespace becomes hyphens."""
        assert slugify("Multiple   Spaces") == "multiple-spaces"
        assert slugify("Tabs\tHere") == "tabs-here"
        assert slugify("Underscore_Test") == "underscore-test"

    def test_consecutive_hyphens_collapsed(self) -> None:
        """Test that consecutive hyphens are collapsed."""
        assert slugify("Test -- Double") == "test-double"
        assert slugify("Test - - - Many") == "test-many"

    def test_leading_trailing_hyphens_removed(self) -> None:
        """Test that leading/trailing hyphens are removed."""
        assert slugify("-Leading") == "leading"
        assert slugify("Trailing-") == "trailing"
        assert slugify("-Both-") == "both"

    def test_long_title_truncation(self) -> None:
        """Test that long titles are truncated at word boundary."""
        long_title = (
            "This is an extremely long article title that should be truncated at sixty chars"
        )
        slug = slugify(long_title)
        assert len(slug) <= 60
        # Should not end with a partial word
        assert not slug.endswith("-")

    def test_empty_string(self) -> None:
        """Test handling of empty string."""
        assert slugify("") == ""

    def test_only_special_chars(self) -> None:
        """Test handling of string with only special characters."""
        assert slugify("!@#$%") == ""


class TestClassifyTopic:
    """Tests for classify_topic function."""

    def test_vlan_classification(self) -> None:
        """Test VLAN topic classification."""
        assert classify_topic("How to Create a VLAN") == "vlans"
        assert classify_topic("Network Configuration Guide") == "vlans"
        assert classify_topic("DHCP Settings") == "vlans"

    def test_firewall_classification(self) -> None:
        """Test firewall topic classification."""
        assert classify_topic("Creating Traffic Rules") == "firewall"
        assert classify_topic("Port Forwarding Setup") == "firewall"
        assert classify_topic("Firewall Best Practices") == "firewall"

    def test_wireless_classification(self) -> None:
        """Test wireless topic classification."""
        assert classify_topic("WiFi Setup Guide") == "wireless"
        assert classify_topic("SSID Configuration") == "wireless"
        assert classify_topic("Access Point Placement") == "wireless"

    def test_switching_classification(self) -> None:
        """Test switching topic classification."""
        assert classify_topic("Switch Port Configuration") == "switching"
        assert classify_topic("PoE Settings") == "switching"
        assert classify_topic("LACP Aggregation") == "switching"

    def test_vpn_classification(self) -> None:
        """Test VPN topic classification."""
        assert classify_topic("WireGuard Setup") == "vpn"
        assert classify_topic("Site-to-Site VPN") == "vpn"
        assert classify_topic("Teleport Configuration") == "vpn"

    def test_gateway_classification(self) -> None:
        """Test gateway topic classification."""
        assert classify_topic("Gateway Settings") == "gateway"
        assert classify_topic("WAN Configuration") == "gateway"
        assert classify_topic("NAT Rules") == "gateway"

    def test_clients_classification(self) -> None:
        """Test clients topic classification."""
        assert classify_topic("Block Client Access") == "clients"
        assert classify_topic("Device Fingerprinting") == "clients"

    def test_system_classification(self) -> None:
        """Test system topic classification."""
        assert classify_topic("Backup Configuration") == "system"
        assert classify_topic("Firmware Update") == "system"
        assert classify_topic("Controller Migration Guide") == "system"

    def test_troubleshooting_classification(self) -> None:
        """Test troubleshooting topic classification."""
        assert classify_topic("Troubleshoot Connection Issues") == "troubleshooting"
        assert classify_topic("Debug Log Analysis") == "troubleshooting"

    def test_fallback_to_general(self) -> None:
        """Test fallback to general topic."""
        assert classify_topic("Random Article Title") == "general"
        assert classify_topic("Something Unrelated") == "general"

    def test_content_affects_classification(self) -> None:
        """Test that content is used for classification."""
        # Ambiguous title, but content mentions firewall
        result = classify_topic(
            "Configuration Guide",
            content="This guide explains how to set up firewall rules",
        )
        assert result == "firewall"

    def test_highest_score_wins(self) -> None:
        """Test that topic with highest keyword score wins."""
        # Multiple keywords for vlans, only one for firewall
        result = classify_topic("VLAN Network DHCP Configuration with Firewall")
        assert result == "vlans"  # 3 keywords vs 1


class TestGenerateSemanticPath:
    """Tests for generate_semantic_path function."""

    def test_basic_path_generation(self) -> None:
        """Test basic semantic path generation."""
        path = generate_semantic_path(
            title="How to Create a VLAN",
            base_dir="help-center",
        )
        assert path == "help-center/vlans/how-to-create-a-vlan.md"

    def test_path_with_content_classification(self) -> None:
        """Test path generation using content for classification."""
        path = generate_semantic_path(
            title="Configuration Guide",
            content="This guide explains how to set up firewall rules",
            base_dir="help-center",
        )
        assert path == "help-center/firewall/configuration-guide.md"

    def test_custom_base_dir(self) -> None:
        """Test path generation with custom base directory."""
        path = generate_semantic_path(
            title="WiFi Setup",
            base_dir="docs/vendor",
        )
        assert path == "docs/vendor/wireless/wifi-setup.md"

    def test_general_topic_path(self) -> None:
        """Test path generation for general topic."""
        path = generate_semantic_path(
            title="Miscellaneous Information",
        )
        assert path == "help-center/general/miscellaneous-information.md"


class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_basic_keyword_extraction(self) -> None:
        """Test basic keyword extraction."""
        keywords = extract_keywords(
            "How to Configure VLAN",
            "Set up DHCP and DNS for your network",
        )
        assert "vlan" in keywords
        assert "dhcp" in keywords
        assert "dns" in keywords
        assert "network" in keywords

    def test_keyword_limit(self) -> None:
        """Test that keywords are limited to 10."""
        # Content with many keywords
        content = (
            "vlan network firewall switch port wifi wireless ssid vpn "
            "gateway wan dhcp dns nat routing"
        )
        keywords = extract_keywords("Complete Guide", content)
        assert len(keywords) <= 10

    def test_no_keywords_found(self) -> None:
        """Test when no keywords are found."""
        keywords = extract_keywords("Random text with no technical terms")
        assert keywords == []

    def test_case_insensitive(self) -> None:
        """Test that keyword extraction is case insensitive."""
        keywords = extract_keywords("VLAN DHCP DNS")
        assert "vlan" in keywords
        assert "dhcp" in keywords
        assert "dns" in keywords


class TestTopicConstants:
    """Tests for topic constant dictionaries."""

    def test_topic_keywords_not_empty(self) -> None:
        """Test that all topics have keywords defined."""
        for topic, keywords in TOPIC_KEYWORDS.items():
            assert len(keywords) > 0, f"Topic {topic} has no keywords"

    def test_topic_descriptions_complete(self) -> None:
        """Test that all topics have descriptions."""
        # All keyword topics should have descriptions
        for topic in TOPIC_KEYWORDS:
            assert topic in TOPIC_DESCRIPTIONS, f"Topic {topic} missing description"
        # General topic should also have description
        assert "general" in TOPIC_DESCRIPTIONS

    def test_descriptions_are_strings(self) -> None:
        """Test that all descriptions are non-empty strings."""
        for topic, description in TOPIC_DESCRIPTIONS.items():
            assert isinstance(description, str), f"Topic {topic} description not string"
            assert len(description) > 0, f"Topic {topic} has empty description"
