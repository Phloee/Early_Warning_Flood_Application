import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

enum StatusType { safe, warning, critical }

class StatusBadge extends StatelessWidget {
  final String text;
  final StatusType type;

  const StatusBadge({
    super.key,
    required this.text,
    required this.type,
  });

  Color get _color {
    switch (type) {
      case StatusType.safe:
        return AppColors.safe;
      case StatusType.warning:
        return AppColors.warning;
      case StatusType.critical:
        return AppColors.critical;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        text.toUpperCase(),
        style: TextStyle(
          color: _color,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
