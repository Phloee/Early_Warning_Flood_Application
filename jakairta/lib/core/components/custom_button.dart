import 'package:flutter/material.dart';

class CustomButton extends StatelessWidget {
  final VoidCallback onPressed;
  final String text;
  final bool isSecondary;

  const CustomButton({
    super.key,
    required this.onPressed,
    required this.text,
    this.isSecondary = false,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: isSecondary 
              ? Theme.of(context).colorScheme.secondary 
              : Theme.of(context).primaryColor,
          elevation: 0,
        ),
        onPressed: onPressed,
        child: Text(text),
      ),
    );
  }
}
